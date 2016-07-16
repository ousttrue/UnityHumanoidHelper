using UnityEngine;
using System.Collections;
using UnityEditor;
using System.Collections.Generic;
using System;
using System.Linq;
using System.Text;

public static class CopyHumanoid
{
    class Node : IEnumerable
    {
        public IEnumerator GetEnumerator()
        {
            throw new NotImplementedException();
        }

        public HumanBodyBones Bone;
        public List<Node> Children;

        public Node(HumanBodyBones bone)
        {
            Bone = bone;
            Children = new List<Node>();
        }

        public void Add(Node child)
        {
            Children.Add(child);
        }
    }

    class BonePosition
    {
        public bool Enable;
        public HumanBodyBones Bone;
        public Vector3 Position;
        public IEnumerable<BonePosition> Children;

        public String ToJSON(int level = 0)
        {
            var sb = new StringBuilder();
            var indent = String.Join("", Enumerable.Range(0, level).Select(_ => "  ").ToArray());
            sb.AppendLine(indent + "{");
            sb.AppendLine(indent + String.Format("  \"name\": \"{0}\"", Bone));
            if (Enable)
            {
                sb.AppendLine(indent + String.Format("  , \"pos\": [{0}, {1}, {2}]"
                    , Position.x, Position.y, Position.z));
            }
            if (Children.Any())
            {
                sb.AppendLine(indent + "  , \"children\": [");
                bool isFirst = true;
                foreach (var child in Children)
                {
                    if (isFirst)
                    {
                        isFirst = false;
                    }
                    else
                    {
                        sb.Append(", ");
                    }
                    sb.Append(child.ToJSON(level + 1));
                }
                sb.AppendLine(indent + "  ]");
            }
            sb.AppendLine(indent + "}");
            return sb.ToString();
        }
    }

    static BonePosition GetPosition(Animator animator, Node node, Vector3 parent)
    {
        var t = animator.GetBoneTransform(node.Bone);
        var p = t != null ? (t.position - parent) : Vector3.zero;
        var bone = new BonePosition
        {
            Bone = node.Bone,
            Enable = t!=null,
            Position = p,
            Children = node.Children.Select(x => GetPosition(animator, x, t.position)),
        };
        return bone;
    }

    [MenuItem("Humanoid/Copy")]
    static void HumanoidToClipboard()
    {
        if (Selection.activeGameObject == null)
        {
            Debug.Log("no selected object");
            return;
        }
        var selected = Selection.activeTransform.gameObject;
        var animator = selected.GetComponent<Animator>();
        if (animator == null)
        {
            Debug.LogWarningFormat("{0} does not has a animator", selected);
            return;
        }

        var json = (GetPosition(animator, new Node(HumanBodyBones.Hips)
        {
            new Node(HumanBodyBones.Spine)
            {
                new Node(HumanBodyBones.Chest)
                {
                    new Node(HumanBodyBones.Neck)
                    {
                        new Node(HumanBodyBones.Head)
                        {
                            new Node(HumanBodyBones.LeftEye)
                            , new Node(HumanBodyBones.RightEye)
                            , new Node(HumanBodyBones.Jaw)
                        }
                    }
                    , new Node(HumanBodyBones.LeftUpperArm)
                    {
                        new Node(HumanBodyBones.LeftLowerArm)
                        {
                            new Node(HumanBodyBones.LeftHand) // ToDo: fingers
                        }
                    }
                    , new Node(HumanBodyBones.RightUpperArm)
                    {
                        new Node(HumanBodyBones.RightLowerArm)
                        {
                            new Node(HumanBodyBones.RightHand) // ToDo: fingers
                        }
                    }
                }
            }
            , new Node(HumanBodyBones.LeftUpperLeg)
            {
                new Node(HumanBodyBones.LeftLowerLeg)
                {
                    new Node(HumanBodyBones.LeftFoot)
                    {
                        new Node(HumanBodyBones.LeftToes)
                    }
                }
            }
            , new Node(HumanBodyBones.RightUpperLeg)
            {
                new Node(HumanBodyBones.RightLowerLeg)
                {
                    new Node(HumanBodyBones.RightFoot)
                    {
                        new Node(HumanBodyBones.RightToes)
                    }
                }
            }
        }, animator.transform.position).ToJSON());

        // copy to clipboard
        GUIUtility.systemCopyBuffer = json;

        Debug.Log("copy skeleton json to clipboard");
        Debug.Log(GUIUtility.systemCopyBuffer);
    }
}
